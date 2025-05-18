'use client'

import { useEffect } from "react";

export default function CookieWidget() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "//embeds.iubenda.com/widgets/a531f893-4eac-4a3c-9210-818b1a245efb.js";
    script.type = "text/javascript";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  return null; // Questo componente non ha output visivo, serve solo a caricare lo script
}