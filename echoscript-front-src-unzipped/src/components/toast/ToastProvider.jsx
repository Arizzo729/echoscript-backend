// src/components/toast/ToastProvider.jsx
import React, {
  createContext,
  useContext,
  useReducer,
  useRef,
  useCallback
} from 'react';

// 1. Create and export context
export const ToastContext = createContext({
  toasts: [],
  addToast: () => {},
  removeToast: () => {}
});

// 2. Hook for components to fire toasts
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx.addToast;
}

// 3. Reducer to manage toast list
function toastReducer(state, action) {
  switch (action.type) {
    case 'ADD':
      return [...state, action.payload];
    case 'REMOVE':
      return state.filter(t => t.id !== action.payload);
    default:
      return state;
  }
}

// 4. Provider component
export function ToastProvider({ children, limit = 5 }) {
  const [toasts, dispatch] = useReducer(toastReducer, []);
  const timers = useRef({});

  const removeToast = useCallback((id) => {
    dispatch({ type: 'REMOVE', payload: id });
    if (timers.current[id]) {
      clearTimeout(timers.current[id]);
      delete timers.current[id];
    }
  }, []);

  const addToast = useCallback(({ message = '', type = 'info', duration = 4000, action } = {}) => {
    const id = `${Date.now()}-${Math.random()}`;
    const toast = { id, message, type, duration, action };
    dispatch({ type: 'ADD', payload: toast });
    timers.current[id] = setTimeout(() => removeToast(id), duration);

    // enforce max count
    if (toasts.length >= limit) {
      const [oldest] = toasts;
      removeToast(oldest.id);
    }
  }, [limit, toasts, removeToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

