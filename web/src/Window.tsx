import type { ReactNode } from "react";

import type { Connection } from "./eventStream";

/** The frame both windows share: who this is, and whether it is still hearing. */
export function Window({
  title,
  connection,
  children,
}: {
  title: string;
  connection: Connection;
  children: ReactNode;
}) {
  return (
    <main className="window">
      <header>
        <h1>{title}</h1>
        <span className={`connection ${connection}`}>{connection}</span>
      </header>
      {children}
    </main>
  );
}
