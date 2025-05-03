"use client";

import { useState, FormEvent } from "react";
import Head from "next/head";
import { signupWithEmailAndPassword, loginWithGoogle} from "../../lib/firebase";


export default function SignUpPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSignUp = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await signupWithEmailAndPassword(email, password);
      // qui puoi fare redirect o altre azioni dopo la registrazione
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleGoogleSignUp = async () => {
    setError(null);
    try {
      await loginWithGoogle();
      // qui puoi fare redirect o altre azioni dopo il login Google
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <>
      <Head>
        <title>Sign Up</title>
        <link rel="icon" href="/logo.png" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
        {error && (
          <div className="w-full rounded-lg bg-red-200 p-6">
            <h5 className="text-red-900 font-bold">{error}</h5>
          </div>
        )}

        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <h1 className="font-extrabold text-indigo-600 text-3xl text-center">Parallax</h1>
          <h2 className="mt-2 text-center text-2xl/9 tracking-tight text-gray-900">
            Sign up to your account
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
          <form
            onSubmit={handleSignUp}
            className="space-y-6"
          >
           <div className="space-y-4">
            <div>
                <label
                  htmlFor="email"
                  className="block text-sm/6 font-medium text-gray-900"
                >
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
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm/6 font-medium text-gray-900"
                >
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  placeholder="Password"
                  className="block w-full bg-red rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-black-300 placeholder:text-black-400 focus:outline-2 focus:-outline-offset-2 focus:outline-black-600 sm:text-sm/6"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2 mt-4 rounded-md bg-indigo-600 text-white">
              Sign up
            </button>

            <div className="flex items-center my-4 text-sm text-gray-500">
              <div className="flex-grow border-t"></div>
              <span className="mx-2">Or continue with</span>
              <div className="flex-grow border-t"></div>
            </div>

            <button
              type="button"
              onClick={handleGoogleSignUp}
              className="w-full flex items-center justify-center py-2 border rounded-md bg-white text-gray-700 hover:bg-gray-100">
              <img
                src="https://www.svgrepo.com/show/355037/google.svg"
                alt="Google"
                className="h-5 w-5 mr-2"
              />
              Google
            </button>
          </form>

          <p className="mt-10 text-center text-sm/6 text-gray-500">
            Already have an account?{" "}
            <a
              href="/login"
              className="font-semibold text-indigo-600 hover:text-indigo-800"
            >
              Sign in
            </a>
          </p>
        </div>
        </div>
    </>
  );
}
