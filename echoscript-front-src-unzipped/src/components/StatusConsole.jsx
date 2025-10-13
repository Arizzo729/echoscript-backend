import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, AlertTriangle, Info } from 'lucide-react';

const LOG_LEVELS = {
  info: { icon: <Info className="text-blue-500" />, color: 'text-blue-500' },
  warning: { icon: <AlertTriangle className="text-yellow-500" />, color: 'text-yellow-500' },
  error: { icon: <AlertTriangle className="text-red-600" />, color: 'text-red-600' },
};

const LOG_LIMIT = 500; // NEW: keep memory/DOM growth in check

function generateRandomLog() {
  const levels = Object.keys(LOG_LEVELS);
  const level = levels[Math.floor(Math.random() * levels.length)];
  const messages = {
    info: [
      'Connected to server.',
      'User authentication successful.',
      'Fetched 100 records.',
      'Background job completed.',
    ],
    warning: [
      'Latency is higher than usual.',
      'API rate limit approaching.',
      'Partial data received.',
    ],
    error: [
      'Failed to fetch data from API.',
      'Unhandled exception occurred.',
      'Database connection lost.',
    ],
  };
  const message = messages[level][Math.floor(Math.random() * messages[level].length)];
  return {
    id: crypto.randomUUID?.() || Math.random().toString(36).slice(2),
    level,
    message,
    timestamp: new Date().toISOString(),
  };
}

export function StatusConsole() {
  const [logs, setLogs] = useState([]);
  const [filterText, setFilterText] = useState('');
  const [filterLevel, setFilterLevel] = useState('all');
  const [collapsedGroups, setCollapsedGroups] = useState({});
  const scrollRef = useRef(null);

  // Auto-generate logs (demo)
  useEffect(() => {
    const interval = setInterval(() => {
      setLogs((prev) => {
        const next = [...prev, generateRandomLog()];
        // Keep only the last LOG_LIMIT entries
        if (next.length > LOG_LIMIT) next.splice(0, next.length - LOG_LIMIT);
        return next;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  // Group logs by date
  const groupedLogs = useMemo(() => {
    const groups = {};
    logs.forEach((log) => {
      const dateKey = log.timestamp.split('T')[0];
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(log);
    });
    return groups;
  }, [logs]);

  // Filter logs
  const filteredGroups = useMemo(() => {
    const search = filterText.toLowerCase();
    const filtered = {};
    for (const [date, logList] of Object.entries(groupedLogs)) {
      const match = logList.filter(
        (log) =>
          log.message.toLowerCase().includes(search) &&
          (filterLevel === 'all' || log.level === filterLevel)
      );
      if (match.length > 0) filtered[date] = match;
    }
    return filtered;
  }, [filterText, filterLevel, groupedLogs]);

  const toggleGroup = (date) =>
    setCollapsedGroups((prev) => ({ ...prev, [date]: !prev[date] }));

  return (
    <div className="flex flex-col max-w-4xl mx-auto p-6 bg-white dark:bg-zinc-800 rounded-lg shadow-lg">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-4">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Status Console</h2>
        <div className="flex gap-3 items-center flex-wrap">
          <div className="relative text-zinc-600 dark:text-zinc-400">
            <input
              type="text"
              placeholder="Search logs..."
              className="pl-9 pr-3 py-2 rounded-md border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
            />
            <Search className="absolute left-2 top-2.5 pointer-events-none" size={16} />
          </div>

          <select
            className="py-2 px-3 rounded-md border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            aria-label="Filter log level"
          >
            <option value="all">All Levels</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>
      </header>

      {/* Log Viewer */}
      <div
        ref={scrollRef}
        className="h-96 overflow-y-auto bg-zinc-100 dark:bg-zinc-900 rounded-md p-4 font-mono text-sm text-zinc-900 dark:text-zinc-100"
        aria-live="polite"
      >
        {Object.entries(filteredGroups).length === 0 ? (
          <p className="text-center text-zinc-500 dark:text-zinc-600 italic select-none">
            No logs found
          </p>
        ) : (
          Object.entries(filteredGroups).map(([date, logList]) => {
            const isCollapsed = collapsedGroups[date];
            return (
              <div key={date} className="mb-6">
                <button
                  onClick={() => toggleGroup(date)}
                  aria-expanded={!isCollapsed}
                  className="flex justify-between w-full font-semibold text-zinc-800 dark:text-zinc-200 mb-2 hover:text-blue-600 dark:hover:text-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                >
                  <span>
                    {new Date(date).toLocaleDateString(undefined, {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                  <span>{isCollapsed ? '+' : '-'}</span>
                </button>

                <AnimatePresence initial={false}>
                  {!isCollapsed && (
                    <motion.ul
                      key="log-list"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-2"
                    >
                      {logList.map(({ id, level, message, timestamp }) => (
                        <motion.li
                          key={id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          className={`flex items-center gap-2 p-2 rounded-md border border-transparent hover:border-zinc-400 dark:hover:border-zinc-600 ${LOG_LEVELS[level].color}`}
                        >
                          <span aria-hidden="true">{LOG_LEVELS[level].icon}</span>
                          <time dateTime={timestamp} className="text-xs flex-shrink-0 w-28 opacity-70">
                            {new Date(timestamp).toLocaleTimeString()}
                          </time>
                          <p className="flex-grow">{message}</p>
                        </motion.li>
                      ))}
                    </motion.ul>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

