// src/components/ErrorBoundary.jsx
import React from "react";
import PropTypes from "prop-types";
// Optional: Uncomment if using Sentry
// import * as Sentry from "@sentry/react";

const ENABLE_SENTRY = true;       // Toggle to false if not using Sentry
const AUTO_RETRY_MS = 3000;       // Auto-retry after 3 seconds

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorInfo: null, retrying: false };
    this.timeout = null;
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, errorInfo: error };
  }

  componentDidCatch(error, info) {
    console.error("🔴 Error caught in ErrorBoundary:", error, info);
    if (ENABLE_SENTRY && typeof Sentry !== "undefined") {
      Sentry.captureException(error);
    }

    this.setState({ retrying: true });
    this.timeout = setTimeout(() => {
      this.setState({ hasError: false, errorInfo: null, retrying: false });
      // Optional: window.location.reload(); // for hard reset
    }, AUTO_RETRY_MS);
  }

  componentWillUnmount() {
    if (this.timeout) clearTimeout(this.timeout);
  }

  handleManualReset = () => {
    this.setState({ hasError: false, errorInfo: null, retrying: false });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center text-white px-4 md:px-8 animate-fade-in">
          <h2 className="text-2xl font-semibold text-red-500 mb-2">
            ⚠️ Something went wrong
          </h2>
          <p className="text-zinc-400 mb-4 text-base">
            Attempting to auto-recover... or{" "}
            <button
              onClick={this.handleManualReset}
              className="underline text-teal-400 hover:text-teal-300"
            >
              refresh now
            </button>
          </p>
          {this.state.retrying && (
            <div className="animate-spin w-8 h-8 border-4 border-teal-400 border-t-transparent rounded-full" />
          )}
          <details className="mt-4 w-full max-w-md text-left text-xs text-zinc-300">
            <summary className="cursor-pointer underline">
              View error details
            </summary>
            <pre className="whitespace-pre-wrap mt-2 bg-zinc-800 p-2 rounded text-[0.65rem]">
              {this.state.errorInfo?.toString()}
              {"\n"}
              {this.state.errorInfo?.stack}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ErrorBoundary;
