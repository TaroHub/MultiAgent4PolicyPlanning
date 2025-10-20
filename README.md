# Multi-Agent Policy Planning System

A sophisticated AI-powered system that uses multiple agents to develop and evaluate municipal policies based on citizen input. The system simulates policy development processes by creating diverse stakeholder perspectives and conducting comprehensive evaluations.

## 🌟 Features

- **Multi-Agent Policy Development**: Collaborative policy creation using specialized AI agents
- **Demographic Analysis**: Automatic investigation of target area demographics and cultural considerations
- **Citizen Simulation**: Generation of diverse virtual citizens for policy evaluation
- **Legal & Feasibility Review**: Automated compliance and feasibility assessment
- **Long-term Impact Analysis**: 10-year future evaluation simulation
- **Real-time Streaming**: Live progress updates during policy development
- **Web Interface**: User-friendly web application for policy input and results visualization

## 🏗️ System Architecture

### Core Components

1. **Research Agent**: Investigates similar policies from other municipalities
2. **Demographics Agent**: Analyzes target area population and cultural trends
3. **Supervisor Agent**: Generates agent definitions based on demographic data
4. **Policy Agents**: Collaborative policy development using swarm intelligence
5. **Reviewer Agent**: Legal compliance and feasibility assessment
6. **Citizen Agents**: Diverse virtual citizens for policy evaluation
7. **Future Evaluation**: Long-term impact simulation

### Evaluation Framework

The system evaluates policies across five key dimensions:
- **Transparency & Accountability** (20%)
- **Ethical Acceptability & Social Acceptance** (10%)
- **Effectiveness & Results** (25%)
- **Equity** (25%)
- **Sustainability & Cost Efficiency** (15%)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- Required Python packages (see requirements below)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MultiAgent4PolicyPlanning
```

2. Install dependencies:
```bash
pip install bedrock-agentcore strands strands-tools flask boto3
```

3. Set up AWS credentials and environment variables:
```bash
export AWS_REGION=us-west-2
export AGENT_ARN=your-agent-arn
```

### Running the Application

#### Option 1: Web Interface
```bash
cd UI
python web_app_en.py
```
Access the web interface at `http://localhost:5000`

#### Option 2: Direct Agent Runtime
```bash
python multi_agent_app_enhanced_en.py
```

## 💻 Usage

### Web Interface

1. Open the web application in your browser
2. Enter citizen input describing policy challenges or needs
3. Click "Start Policy Evaluation" to begin the process
4. Monitor real-time progress through the streaming interface
5. Review comprehensive results including:
   - Generated policy proposal
   - Agent definitions
   - Citizen evaluations
   - Legal review results
   - Final assessment scores

### Example Input

```
Tokyo is facing the following challenges due to the increase in foreign residents. Please develop policies to address these issues:
- Multilingual support for Japanese language assistance, administrative procedures, and disaster response is insufficient.
- Cultural friction occurs in daily life support and educational settings.
```

## 📊 Output Structure

The system generates comprehensive policy evaluation reports including:

### Policy Proposal
- Policy title and summary
- Problem analysis
- Detailed policy description
- Implementation plan
- Expected effects
- Referenced similar policies

### Agent Evaluations
- **Policy Agents**: Specialized experts for policy development
- **Citizen Agents**: Diverse virtual citizens (10+ agents) representing different demographics
- **Reviewer Agent**: Legal and feasibility assessment

### Evaluation Metrics
- Personal impact scores
- Family impact assessment
- Community impact analysis
- Fairness evaluation
- Sustainability assessment
- 10-year future projections

## 🔧 Configuration

### Model Configuration
The system uses Claude Sonnet 4 (us.anthropic.claude-sonnet-4-20250514-v1:0) for all agent interactions.

### Agent Generation Rules
- **Policy Agents**: 2-4 specialized experts including Tokyo administration perspective
- **Citizen Agents**: Minimum 10 diverse virtual citizens based on demographic data
- **Demographic Balance**: Represents various age groups, family structures, and cultural backgrounds

## 📁 Project Structure

```
MultiAgent4PolicyPlanning/
├── multi_agent_app_enhanced_en.py    # Main agent runtime application
├── UI/
│   ├── web_app_en.py                 # Flask web application
│   └── index_en.html                 # Web interface
└── README.md                         # This file
```

## 🔍 Key Features Detail

### Demographic Analysis
- Automatic target area identification
- Age and gender distribution analysis
- Language proficiency assessment
- Cultural consideration mapping
- Priority service identification

### Policy Development Process
1. **Research Phase**: Investigation of similar municipal policies
2. **Analysis Phase**: Demographic trend analysis
3. **Generation Phase**: Agent definition creation
4. **Development Phase**: Collaborative policy creation
5. **Review Phase**: Legal and feasibility assessment (up to 3 iterations)
6. **Evaluation Phase**: Multi-perspective citizen evaluation
7. **Future Analysis**: 10-year impact simulation
8. **Final Assessment**: Comprehensive scoring and recommendations

### Scoring System
- **Approval Threshold**: 80+ points for policy approval
- **Recommendation Levels**:
  - 70+ points: Recommended
  - 50-69 points: Conditionally recommended
  - <50 points: Reconsideration recommended

## 🌐 API Integration

The system integrates with AWS Bedrock AgentCore for:
- Streaming response handling
- Agent runtime management
- Model inference coordination

## 🤝 Contributing

This system is designed for municipal policy development and evaluation. Contributions should focus on:
- Enhanced demographic analysis capabilities
- Additional evaluation frameworks
- Improved agent diversity algorithms
- Extended policy domain support

## 📄 License

[Add your license information here]

## 🆘 Support

For technical support or questions about the policy evaluation system, please refer to the AWS Bedrock documentation or contact the development team.

---

*This system is designed to assist in policy development processes and should be used in conjunction with human expertise and official municipal procedures.*