import os
import ast
from typing import List, Dict, Tuple
from pathlib import Path
from repo_checker.schemas import RepositoryArchitectureArtifact, Evidence, EvidenceType

class RepoExtractor:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        
    def extract_deterministic(self) -> RepositoryArchitectureArtifact:
        evidence_list = []
        components = set()
        databases = set()
        frameworks = set()
        manifests_found = []
        
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            manifests_found.append("requirements.txt")
            with open(req_file, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip().lower()
                    if not line or line.startswith('#'):
                        continue
                        
                    if "psycopg" in line or "postgresql" in line:
                        databases.add("PostgreSQL")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="PostgreSQL driver",
                            confidence=1.0
                        ))
                    elif "pymongo" in line or "motor" in line:
                        databases.add("MongoDB")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="MongoDB driver",
                            confidence=1.0
                        ))
                    elif "redis" in line:
                        databases.add("Redis")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="Redis client",
                            confidence=1.0
                        ))
                    elif "elasticsearch" in line:
                        databases.add("Elasticsearch")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="Elasticsearch client",
                            confidence=1.0
                        ))
                    elif "kafka" in line:
                        components.add("Kafka")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="Kafka client",
                            confidence=1.0
                        ))
                        
                    if "fastapi" in line:
                        frameworks.add("FastAPI")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="FastAPI",
                            confidence=1.0
                        ))
                    elif "flask" in line:
                        frameworks.add("Flask")
                        evidence_list.append(Evidence(
                            source_file="requirements.txt",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="Flask",
                            confidence=1.0
                        ))
                        
        pkg_file = self.repo_path / "package.json"
        if pkg_file.exists():
            manifests_found.append("package.json")
            import json
            try:
                with open(pkg_file, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)
                    deps = pkg_data.get('dependencies', {})
                    dev_deps = pkg_data.get('devDependencies', {})
                    all_deps = {**deps, **dev_deps}
                    
                    for dep in all_deps:
                        dep_lower = dep.lower()
                        if "express" in dep_lower:
                            frameworks.add("Express")
                            evidence_list.append(Evidence(
                                source_file="package.json", location=dep, evidence_type=EvidenceType.DEPENDENCY_DECLARED, observed_entity="Express", confidence=1.0
                            ))
                        if "pg" in dep_lower or "sequelize" in dep_lower:
                            databases.add("PostgreSQL")
                            evidence_list.append(Evidence(
                                source_file="package.json", location=dep, evidence_type=EvidenceType.DEPENDENCY_DECLARED, observed_entity="PostgreSQL driver", confidence=1.0
                            ))
                        if "mongodb" in dep_lower or "mongoose" in dep_lower:
                            databases.add("MongoDB")
                            evidence_list.append(Evidence(
                                source_file="package.json", location=dep, evidence_type=EvidenceType.DEPENDENCY_DECLARED, observed_entity="MongoDB driver", confidence=1.0
                            ))
            except Exception:
                pass
                
        docker_file = self.repo_path / "Dockerfile"
        if docker_file.exists():
            with open(docker_file, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip().lower()
                    if "python" in line and "from" in line:
                        frameworks.add("Python")
                        evidence_list.append(Evidence(
                            source_file="Dockerfile",
                            location=f"line {line_no}",
                            evidence_type=EvidenceType.DEPENDENCY_DECLARED,
                            observed_entity="Python base image",
                            confidence=1.0
                        ))
                        
        for py_file in self.repo_path.rglob("*.py"):
            if "venv" in py_file.parts or ".env" in py_file.parts:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self._check_import(alias.name, py_file, node.lineno, evidence_list, databases, frameworks, components)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                self._check_import(node.module, py_file, node.lineno, evidence_list, databases, frameworks, components)
            except Exception:
                pass
                        
        components.update(frameworks)
        components.update(databases)
        
        return RepositoryArchitectureArtifact(
            components=list(components),
            databases=list(databases),
            frameworks=list(frameworks),
            evidence=evidence_list,
            manifests_found=manifests_found
        )
        
    def _check_import(self, module_name: str, py_file: Path, lineno: int, evidence_list: List, databases: set, frameworks: set, components: set):
        module_name = module_name.lower()
        rel_path = str(py_file.relative_to(self.repo_path))
        
        if "fastapi" in module_name:
            frameworks.add("FastAPI")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="FastAPI", confidence=1.0))
        elif "flask" in module_name:
            frameworks.add("Flask")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="Flask", confidence=1.0))
        elif "psycopg" in module_name:
            databases.add("PostgreSQL")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="PostgreSQL driver", confidence=1.0))
        elif "pymongo" in module_name:
            databases.add("MongoDB")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="MongoDB driver", confidence=1.0))
        elif "redis" in module_name:
            databases.add("Redis")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="Redis client", confidence=1.0))
        elif "kafka" in module_name:
            components.add("Kafka")
            evidence_list.append(Evidence(source_file=rel_path, location=f"line {lineno}", evidence_type=EvidenceType.IMPORT_OBSERVED, observed_entity="Kafka client", confidence=1.0))
