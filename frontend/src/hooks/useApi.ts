import { useEffect, useState } from "react";
import { api } from "../api/client";

export function useApi<T>(path: string | null, fallback: T) {
  const [data, setData] = useState<T>(fallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!path) {
      setData(fallback);
      setLoading(false);
      setError(null);
      return;
    }
    const controller = new AbortController();
    setData(fallback);
    setLoading(true);
    setError(null);
    api<T>(path, { signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => {
      controller.abort();
    };
  }, [path]);

  return { data, setData, loading, error };
}
