import React from 'react';
import './LeftSection.css';

interface TeamMember {
	name: string;
	role: string;
	avatar: string;
	linkedin: string;
	email: string;
	github: string;
}

const teamMembers: TeamMember[] = [
	{
		name: 'Sarah Johnson',
		role: 'AI Developer',
		avatar: 'SJ',
		linkedin: 'linkedin.com/in/sarahjohnson',
		email: 'sarah@travelbot.com',
		github: 'github.com/sarahjohnson',
	},
	{
		name: 'Michael Chen',
		role: 'Web Developer',
		avatar: 'MC',
		linkedin: 'linkedin.com/in/michaelchen',
		email: 'michael@travelbot.com',
		github: 'github.com/michaelchen',
	},
];

const LeftSection: React.FC = () => {
	return (
		<div className='left-section'>
			<div className='header-section'>
				<h1 className='app-title'>Travel Bot</h1>
				<p className='app-subtitle'>
					Your AI-powered travel planning assistant
				</p>
			</div>

			<div className='team-section'>
				<h2 className='team-title'>Development Team</h2>
				<div className='team-members'>
					{teamMembers.map((member, index) => (
						<div key={index} className='team-member'>
							<div className='avatar'>
								<span className='avatar-text'>{member.avatar}</span>
							</div>
							<div className='member-info'>
								<h3 className='member-name'>{member.name}</h3>
								<p className='member-role'>{member.role}</p>
								<div className='member-contacts'>
									<a
										href={`https://${member.linkedin}`}
										className='contact-link'
										target='_blank'
										rel='noopener noreferrer'
									>
										<span className='contact-icon'>💼</span>
										{member.linkedin}
									</a>
									<a href={`mailto:${member.email}`} className='contact-link'>
										<span className='contact-icon'>✉️</span>
										{member.email}
									</a>
									<a
										href={`https://${member.github}`}
										className='contact-link'
										target='_blank'
										rel='noopener noreferrer'
									>
										<span className='contact-icon'>🐱</span>
										{member.github}
									</a>
								</div>
							</div>
						</div>
					))}
				</div>
			</div>
		</div>
	);
};

export default LeftSection;
