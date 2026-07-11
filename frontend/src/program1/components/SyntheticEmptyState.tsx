export function SyntheticEmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="program1-empty" role="status">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}
