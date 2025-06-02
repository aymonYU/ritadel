import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/analysis');
  }, [router]);

  return null; // Return null since we're redirecting
} 