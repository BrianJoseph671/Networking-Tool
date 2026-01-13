# Usage Guide: Multi-Agent Networking Tool

## Quick Start

### 1. Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API key:**
   - Open the `.env` file
   - Replace `your_api_key_here` with your actual Anthropic API key

3. **Start the server:**
   ```bash
   python -m backend.main
   ```

4. **Open in browser:**
   - Navigate to `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

### 2. Workflow

#### Step 1: Add a Prospect

1. Click "Add Prospect" button
2. Enter basic information:
   - Name (required)
   - Email, LinkedIn URL, Company, Title (optional)
3. Click "Add Prospect"

#### Step 2: Add Research Data

1. Go to the "Research" tab
2. Select the prospect from the dropdown
3. Choose a research agent:
   - **LinkedIn Agent**: For professional profile data
   - **Google Agent**: For projects, publications, web presence
   - **Social Media Agent**: For interests and personality insights

4. Paste the research data (can be raw text from their profile)
5. Click "Process Research Data"

**Example LinkedIn Data:**
```
John Smith
Senior Software Engineer at Tech Corp
San Francisco, CA

Experience:
- Senior Software Engineer at Tech Corp (2020-Present)
  Building scalable microservices, leading team of 5 engineers
- Software Engineer at StartupXYZ (2017-2020)
  Full-stack development, React and Node.js

Education:
- BS Computer Science, Stanford University (2017)

Skills: Python, JavaScript, React, AWS, Docker, Kubernetes
```

**Tip:** You can add multiple research data types for the same prospect. The more data, the better the persona!

#### Step 3: Generate Persona

1. Go back to "Prospects" tab
2. Click "Generate Persona" button for your prospect
3. Wait for the AI to analyze all research data
4. Click "View Persona" to see the results

The persona includes:
- Professional summary
- Expertise areas
- Personality traits
- Communication style
- Connection strategy
- Conversation starters

#### Step 4: Generate Messages

1. Go to "Messages" tab
2. Select the prospect (must have persona generated)
3. Configure message parameters:
   - **Channel**: LinkedIn, Email, or Twitter
   - **Tone**: Professional, Casual, Warm, or Direct
   - **Familiarity**: Stranger, Acquaintance, Colleague, or Friend
   - **Connection Degree**: 1st, 2nd, or 3rd+ degree
   - **Custom Context**: Add any specific context (optional)

4. Click "Generate Message"
5. Review the personalized message
6. Use "Copy Message" to copy it
7. Click "Mark as Sent" after sending it

#### Step 5: Track Performance

1. Go to "Analytics" tab
2. Click "Refresh Analytics"
3. View metrics:
   - Total messages sent
   - Response rate
   - Follow-ups needed
   - Performance insights
   - Recommendations

## Tips for Best Results

### Research Data Tips

1. **LinkedIn Data** - Include:
   - Current and past job titles
   - Company names and employment dates
   - Education details
   - Skills and certifications
   - Notable projects or achievements

2. **Google/Web Data** - Include:
   - Links to personal website/blog
   - GitHub profile
   - Published articles or papers
   - Conference talks or podcasts
   - News mentions

3. **Social Media Data** - Include:
   - Recent posts or tweets
   - Topics they engage with
   - Causes they support
   - Hobbies or interests mentioned
   - Communication style examples

### Message Generation Tips

1. **Channel Selection:**
   - **LinkedIn**: More professional, reference work experience
   - **Email**: More flexible, can be longer and detailed
   - **Twitter**: Brief, casual, reference their tweets/interests

2. **Tone Selection:**
   - **Professional**: Formal business relationships
   - **Casual**: Peer-to-peer, similar age/experience
   - **Warm**: Enthusiastic, expressing genuine interest
   - **Direct**: Brief, to-the-point, busy professionals

3. **Custom Context:**
   - Mention mutual connections
   - Reference specific shared interests
   - Add context about why you're reaching out
   - Mention events you both attended

### A/B Testing

To test different messaging strategies:

1. Generate 2-3 messages with different tones for similar prospects
2. Send them and track responses
3. Check Analytics to see which approach works best
4. Use insights to optimize future messages

## Example Workflow

Here's a complete example:

### 1. Add Prospect
```
Name: Sarah Chen
Email: sarah.chen@example.com
LinkedIn: linkedin.com/in/sarahchen
Company: AI Startup Inc
Title: VP of Product
```

### 2. Add LinkedIn Research
```
Sarah Chen
VP of Product at AI Startup Inc
New York, NY

10+ years in product management, focused on AI/ML products
Previously PM at Google, leading search quality initiatives
Stanford MBA, UC Berkeley BS Computer Science

Passionate about ethical AI and diversity in tech
Speaker at ProductCon 2023, author of PM blog
```

### 3. Add Social Media Research
```
Active on Twitter (@sarahchen)
Frequently tweets about:
- Product strategy
- AI ethics
- Women in tech
- San Francisco tech scene

Tone: Thoughtful, analytical, occasionally humorous
Engages with AI safety discussions
Supports STEM education initiatives
```

### 4. Generate Persona
AI creates a comprehensive profile including:
- Career trajectory analysis
- Expertise in AI product management
- Values: ethics, diversity, education
- Communication style: professional but approachable
- Conversation starters: AI ethics, product strategy

### 5. Generate Message (LinkedIn, Professional tone)
AI generates:
```
Hi Sarah,

I came across your recent ProductCon talk on ethical AI in product
development and found your framework fascinating. I'm particularly
interested in how you balance innovation with safety considerations
at AI Startup Inc.

I'm working on similar challenges in [your area] and would love to
hear more about your approach to building AI products with ethical
guardrails from the start.

Would you be open to a brief coffee chat?

Best,
[Your Name]
```

## Troubleshooting

### "ANTHROPIC_API_KEY is required" error
- Make sure you've set your API key in the `.env` file
- Restart the server after updating `.env`

### "Persona must be generated first" error
- You need to add research data first
- Then generate the persona before creating messages

### Messages feel too generic
- Add more detailed research data
- Use the "Custom Context" field to add specific details
- Try different tone/familiarity combinations

### No follow-ups showing
- Make sure you've marked messages as "Sent"
- Wait the configured number of days (default: 3)
- Check the Analytics tab

## Advanced Features

### API Usage

You can also use the API directly:

```bash
# Create a prospect
curl -X POST http://localhost:8000/api/prospects \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Add research data
curl -X POST http://localhost:8000/api/prospects/1/research \
  -H "Content-Type: application/json" \
  -d '{"source_type": "linkedin", "raw_text": "..."}'

# Generate persona
curl -X POST http://localhost:8000/api/prospects/1/persona

# Generate message
curl -X POST http://localhost:8000/api/prospects/1/message \
  -H "Content-Type: application/json" \
  -d '{"channel": "linkedin", "tone": "professional"}'
```

### Database Location

The SQLite database is stored at `./data/networking.db`

To backup your data:
```bash
cp data/networking.db data/networking_backup.db
```

## Best Practices

1. **Start Small**: Test with 1-2 prospects first
2. **Quality Data**: Better research data = better personas and messages
3. **Iterate**: Try different message styles and track what works
4. **Follow Up**: Use the analytics to stay on top of follow-ups
5. **Personalize**: Always review and tweak AI-generated messages before sending

## Next Steps

Once comfortable with the basics:
- Experiment with different agent combinations
- Track A/B test results systematically
- Build a pipeline for regular prospect research
- Use analytics insights to refine your approach

Happy networking!
