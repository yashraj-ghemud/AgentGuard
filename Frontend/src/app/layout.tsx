/**
 * Root Layout
 */

import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentGuard - AI Agent Red-Teaming Platform',
  description: 'Automated Red-Teaming & Reliability Engineering for AI Agents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
