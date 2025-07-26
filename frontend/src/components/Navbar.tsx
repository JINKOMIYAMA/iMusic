
import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Music } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useIsMobile } from "@/hooks/use-mobile";

const Navbar = () => {
  const isMobile = useIsMobile();
  
  return (
    <header className="bg-gradient-to-r from-black via-red-950 to-black border-b border-red-800 sticky top-0 z-10 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link to="/" className="font-bold text-xl flex items-center gap-2 text-white hover:text-red-400 transition-colors">
            <Music className="text-red-600 drop-shadow-lg" />
            <span className="bg-gradient-to-r from-white to-red-100 bg-clip-text text-transparent">iMusic</span>
          </Link>
          
          {isMobile ? (
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm" className="text-white hover:text-red-400 hover:bg-red-950/20">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="4" x2="20" y1="12" y2="12" />
                    <line x1="4" x2="20" y1="6" y2="6" />
                    <line x1="4" x2="20" y1="18" y2="18" />
                  </svg>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="bg-black border-l border-red-800/50 w-[250px] px-4">
                <div className="flex flex-col space-y-4 mt-8">
                  <Button variant="ghost" className="text-white hover:text-red-400 hover:bg-red-950/20 justify-start" asChild>
                    <Link to="/">ホーム</Link>
                  </Button>
                  <Button variant="ghost" className="text-white hover:text-red-400 hover:bg-red-950/20 justify-start" asChild>
                    <Link to="/about">このアプリについて</Link>
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          ) : (
            <nav>
              <ul className="flex space-x-4">
                <li>
                  <Button variant="ghost" className="text-white hover:text-red-400 hover:bg-red-950/20" asChild>
                    <Link to="/">ホーム</Link>
                  </Button>
                </li>
                <li>
                  <Button variant="ghost" className="text-white hover:text-red-400 hover:bg-red-950/20" asChild>
                    <Link to="/about">このアプリについて</Link>
                  </Button>
                </li>
              </ul>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
