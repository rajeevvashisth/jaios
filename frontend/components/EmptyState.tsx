export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-500 dark:border-neutral-700">
      {message}
    </div>
  );
}
