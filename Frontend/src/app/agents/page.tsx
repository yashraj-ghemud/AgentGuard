/**
 * Agents Page
 */

import { AgentList } from '../../modules/agents';

export default function AgentsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <AgentList />
      </div>
    </div>
  );
}
