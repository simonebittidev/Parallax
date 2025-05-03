"use client";

import { useState, FormEvent } from "react";
import Head from "next/head";
import { resetEmail } from "../../lib/firebase";

export default function ResetPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleReset = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);

    try {
      await resetEmail(email);
      setMessage(
        "Controlla la tua casella: ti abbiamo inviato un link per resettare la password."
      );
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <>
      <Head>
        <title>Reset Password</title>
        <link rel="icon" href="/logo.png" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
           
          {error && (
            <div className="w-full rounded-lg bg-red-200 p-6 m-5">
              <h5 className="text-red-900 font-bold">{error}</h5>
            </div>
          )}
          {message && (
            <div className="w-full rounded-lg bg-green-200 p-6 m-5">
              <h5 className="text-green-900 font-bold">{message}</h5>
            </div>
          )}

        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <h1 className="font-extrabold text-indigo-600 text-3xl text-center">Parallax</h1>
          <h2 className="mt-2 text-center text-2xl/9 tracking-tight text-gray-900">
            Reset your password
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
          <form onSubmit={handleReset} className="space-y-6">
          <div className="space-y-4">
              <div>
                <label htmlFor="email"  className="block text-sm/6 font-medium text-gray-900">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="Email"
                  className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-black-300 placeholder:text-black-400 focus:outline-2 focus:-outline-offset-2 focus:outline-black-600 sm:text-sm/6"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2 mt-4 rounded-md bg-indigo-600 text-white">
              Reset Password
            </button>
          </form>
        </div>
        </div>
    </>
  );
}
