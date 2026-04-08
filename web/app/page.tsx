import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";
import { RecommendationApp } from "@/components/RecommendationApp";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <RecommendationApp />
      </main>
      <Footer />
    </div>
  );
}
