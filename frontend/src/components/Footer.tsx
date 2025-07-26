
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

const Footer = () => {
  return (
    <footer className="mt-auto bg-gradient-to-r from-black via-red-950 to-black text-white border-t border-red-800 py-6">
      <div className="container mx-auto px-4">
        <div className="text-center">
          <p className="text-sm text-gray-300">
            &copy; {new Date().getFullYear()} iMusic - YouTube M4A ダウンローダー
          </p>
          <p className="text-xs text-gray-400 mt-1">
            高品質M4A形式でダウンロード、メタデータ・ジャケット画像付き
          </p>
          
          <div className="mt-4 flex flex-col sm:flex-row justify-center items-center gap-2">
            <Button variant="link" size="sm" className="text-xs text-gray-400 hover:text-red-400 transition-colors">
              プライバシーポリシー
            </Button>
            <span className="hidden sm:inline text-gray-600">|</span>
            <Button variant="link" size="sm" className="text-xs text-gray-400 hover:text-red-400 transition-colors">
              利用規約
            </Button>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
