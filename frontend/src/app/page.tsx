import { Suspense } from "react";
import { ExamBrowser } from "@/components/ExamBrowser";
import { Loading } from "@/components/StateViews";

export default function Home() {
  return (
    <Suspense fallback={<Loading />}>
      <ExamBrowser />
    </Suspense>
  );
}
