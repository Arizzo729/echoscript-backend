import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Key, CheckCircle2, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';

export default function VerifyEmail() {
  const { verifyEmail, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // Trigger verify endpoint
      await verifyEmail({ email, code, remember: true });
      setSuccess('✅ Email verified! Redirecting...');
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err) {
      setError(err.message || '⚠️ Verification failed. Please try again.');
    }
  };

  return (
    <motion.div
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-800 px-6"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="w-full max-w-sm p-8 space-y-6 rounded-2xl shadow-xl bg-zinc-900 border border-zinc-700">
        <h1 className="text-2xl font-bold text-center text-white">
          Verify Your Email
        </h1>
        <p className="text-sm text-center text-zinc-400">
          Enter the 6-digit code sent to your email.
        </p>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 text-red-300 px-4 py-2 rounded-md text-sm">
            <XCircle className="w-5 h-5" /> {error}
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2 bg-green-500/10 text-green-300 px-4 py-2 rounded-md text-sm">
            <CheckCircle2 className="w-5 h-5" /> {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-col gap-1">
            <label htmlFor="email" className="text-sm font-medium text-zinc-300">
              Email Address
            </label>
            <div className="relative">
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full px-4 py-2 pr-10 rounded-lg border border-zinc-700 bg-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <Mail className="absolute right-3 top-2.5 w-5 h-5 text-zinc-400" />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="code" className="text-sm font-medium text-zinc-300">
              Verification Code
            </label>
            <div className="relative">
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={6}
                placeholder="123456"
                className="w-full px-4 py-2 pr-10 rounded-lg border border-zinc-700 bg-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <Key className="absolute right-3 top-2.5 w-5 h-5 text-zinc-400" />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            fullWidth
            loading={loading}
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </Button>
        </form>

        <p className="text-xs text-center text-zinc-500">
          Didn’t get a code?{' '}
          <button
            onClick={() => window.location.reload()}
            className="text-teal-400 hover:underline"
          >
            Resend Code
          </button>
        </p>
      </div>
    </motion.div>
  );
}
