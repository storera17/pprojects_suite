/** Describes the Toast data shape so future readers know what fields travel through the app. */
export interface Toast {
  id: number;
  text: string;
  gold?: boolean;
}

/** Describes the ToastsProps data shape so future readers know what fields travel through the app. */
interface ToastsProps {
  toasts: Toast[];
}

/** Floating notification renderer used for confirmations, unlocks, and badge messages. */
export function Toasts({ toasts }: ToastsProps) {
  return (
    <div className="toasts">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${toast.gold ? 'gold' : ''}`}>
          {toast.text}
        </div>
      ))}
    </div>
  );
}

