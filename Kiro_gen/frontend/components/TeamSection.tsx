'use client';

interface TeamMember {
  name: string;
  email: string;
}

const teamMembers: TeamMember[] = [
  { name: 'Sudeep Aryan', email: 'sudeeparyang@gmail.com' },
  { name: 'Varvara Murphy', email: 'vvmurphy@amazon.com' },
  { name: 'Sean Doran', email: 'sean.doran@vi.ie' },
  { name: 'Borja Martin-Lunas', email: 'Borja.Martinlunas@dentsu.com' },
  { name: 'Enda Kenny', email: 'endakenn@amazon.com' },
  { name: 'Eoin Hamdam', email: 'eoin.hamdam@boi.com' },
  { name: 'Bernadette Fitzsimons', email: 'bfitzsimons@merative.com' },
  { name: 'Lina Joe', email: 'ombacchuwargad@gmail.com' },
];

export default function TeamSection() {
  return (
    <section className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg shadow p-8" aria-labelledby="team-heading">
      <div className="mb-8">
        <h2 id="team-heading" className="text-2xl font-bold text-gray-900 mb-4">
          🇮🇪 Team Vision Ireland
        </h2>
        <div className="bg-white rounded-lg p-6 mb-6 border-l-4 border-indigo-500">
          <h3 className="text-lg font-semibold text-indigo-900 mb-2">Our Vision</h3>
          <p className="text-gray-700">
            Making comics accessible to everyone through innovative AI-powered audio narration. 
            We believe that visual storytelling should be experienced by all, regardless of visual ability.
            Our team is dedicated to breaking down barriers and creating inclusive experiences.
          </p>
        </div>
        <div className="bg-white rounded-lg p-6 border-l-4 border-green-500">
          <h3 className="text-lg font-semibold text-green-900 mb-2">Developer Note</h3>
          <p className="text-gray-700">
            This project was built with accessibility at its core, leveraging AWS services including 
            Amazon Bedrock for AI analysis and Amazon Polly for natural voice synthesis. 
            Special thanks to Vision Ireland for their guidance on accessibility best practices.
          </p>
        </div>
      </div>

      <h3 className="text-xl font-semibold text-gray-900 mb-4">Meet the Team</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {teamMembers.map((member, index) => (
          <div
            key={index}
            className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow border border-gray-100"
          >
            <div className="flex items-center mb-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                {member.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div className="ml-3">
                <p className="font-semibold text-gray-900 text-sm">{member.name}</p>
              </div>
            </div>
            <a
              href={`mailto:${member.email}`}
              className="text-xs text-gray-500 hover:text-indigo-600 transition-colors break-all"
              aria-label={`Email ${member.name}`}
            >
              {member.email}
            </a>
          </div>
        ))}
      </div>

      <div className="mt-6 text-center text-sm text-gray-500">
        <p>📞 Contact: +353 899613030 | Dublin, Ireland</p>
      </div>
    </section>
  );
}
