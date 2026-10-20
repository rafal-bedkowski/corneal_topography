import { Suspense } from "react";
import { ExamRouteView } from "@/components/ExamRouteView";
import { Loading } from "@/components/StateViews";

export default function ExamPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ExamRouteView />
    </Suspense>
  );
}
