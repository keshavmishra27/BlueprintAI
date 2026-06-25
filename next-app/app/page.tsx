import { Button } from "@/components/ui/button"
import LaptopAnimation from "@/components/LaptopAnimation"

export default function Page() {
  return (
    <div className="flex min-h-svh p-6 relative overflow-hidden bg-background">
      <div className="flex max-w-md min-w-0 flex-col gap-4 text-sm leading-loose z-10 relative">
        <div>
          <h1 className="font-medium text-4xl mb-4 font-bold tracking-tight">Project ready!</h1>
          <p className="text-muted-foreground text-lg mb-2">You may now add components and start building.</p>
          <p className="text-muted-foreground mb-6">We&apos;ve already added the button component for you.</p>
          <Button className="mt-2 w-fit px-8 rounded-full shadow-lg hover:shadow-xl transition-all">Button</Button>
        </div>
        <div className="font-mono text-xs text-muted-foreground mt-8">
          (Press <kbd className="px-2 py-1 bg-muted rounded border">d</kbd> to toggle dark mode)
        </div>
      </div>

      {}
      <div className="absolute inset-0 z-0 flex items-center justify-end pointer-events-none pr-12">
        <div className="w-1/2 h-full flex items-center justify-center pointer-events-auto">
          <LaptopAnimation />
        </div>
      </div>
    </div>
  )
}
