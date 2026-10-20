import { Suspense } from "react";
import { Loading } from "@/components/StateViews";
import { StatsView } from "@/components/StatsView";

export default function StatsPage() {
  return (
    <Suspense fallback={<Loading />}>
      <StatsView />
    </Suspense>
  );
}
