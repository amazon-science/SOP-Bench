# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Open-source release preparation
- LICENSE file (Apache 2.0)
- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant)
- SECURITY.md with security policy
- GitHub issue templates (bug report, feature request)
- GitHub pull request template
- CHANGELOG.md for tracking changes

### Changed
- Updated .gitignore to exclude temporary files
- Improved documentation structure

### Removed
- Temporary log files and results directories

## [0.1.0] - 2025-01-28

### Added
- Initial release of SOP-Bench
- 10 industrial benchmarks across diverse domains:
  - content_flagging (Content Moderation)
  - customer_service (Support)
  - dangerous_goods (Supply Chain)
  - aircraft_inspection (Transportation)
  - email_intent (Retail)
  - know_your_business (Finance)
  - patient_intake (Healthcare)
  - video_annotation (Autonomous Driving)
  - video_classification (Media)
  - warehouse_inspection (Logistics)
- 1,800+ realistic tasks with ground truth outputs
- Two baseline agent implementations:
  - Function-Calling Agent (Bedrock Converse API)
  - ReAct Agent (reasoning and acting)
- Comprehensive evaluation framework:
  - Task Success Rate (TSR)
  - Execution Completion Rate (ECR)
  - Conditional Task Success Rate (C-TSR)
  - Tool Accuracy metrics
- CLI interface (`sop-bench`) for easy evaluation
- Programmatic API for custom integrations
- Mock tool implementations for reproducible evaluation
- Parallel execution support with `--max-workers`
- Execution trace saving with `--save-traces`
- Detailed documentation:
  - README.md with quick start guide
  - ARCHITECTURE.md with technical details
  - DEVELOPMENT.md for contributors
- Comprehensive test suite
- Python package structure with setup.py
- AWS Bedrock integration for LLM inference
- Support for multiple Claude models

### Research Contributions
- Demonstrated that SOTA LLMs struggle with SOP execution (27-48% TSR)
- Identified key challenges: tool selection, implicit knowledge, branching logic
- Provided baseline implementations for future research
- Published research findings in REACT_AGENT_RESEARCH_FINDINGS.md

### Documentation
- Quick start guide with installation instructions
- Troubleshooting section for common issues
- Examples for programmatic usage
- Guide for adding custom agents and benchmarks
- API reference documentation

### Testing
- Unit tests for benchmark loader
- Unit tests for agent implementations
- Integration tests for evaluation pipeline
- Mock AWS Bedrock responses for testing

### Known Limitations
- Requires AWS Bedrock access
- Currently supports Claude models only
- Mock tools (not real API integrations)
- Limited to English language SOPs

## Release Notes

### Version 0.1.0 - Initial Release

This is the first public release of SOP-Bench, a comprehensive benchmark for evaluating LLM agents on Standard Operating Procedures across 10 industrial domains.

**Key Highlights:**
- 1,800+ realistic tasks spanning content moderation, healthcare, logistics, and more
- Two baseline agent implementations with detailed evaluation metrics
- Easy-to-use CLI and programmatic API
- Reproducible evaluation with mock tools
- Comprehensive documentation and examples

**Getting Started:**
```bash
pip install amazon-sop-bench
./sop-bench list
./sop-bench evaluate content_flagging --agent function_calling --max-tasks 1
```

**Research Paper:**
- arXiv: https://arxiv.org/abs/2506.08119
- AMLC 2025 Oral Presentation

**Citation:**
```bibtex
@article{sopbench2025,
  title={SOP-Bench: Complex Industrial SOPs for Evaluating LLM Agents},
  author={Nandi, Subhrangshu and Datta, Arghya and Vichare, Nikhil and 
          Bhattacharya, Indranil and Raja, Huzefa and Xu, Jing and 
          Ray, Shayan and Carenini, Giuseppe and Srivastava, Abhi and 
          Chan, Aaron and Woo, Man Ho and Kandola, Amar and 
          Theresa, Brandon and Carbone, Francesco},
  journal={arXiv preprint arXiv:2506.08119},
  year={2025}
}
```

**Acknowledgments:**
This work was conducted by the Applied AI team at Amazon. We thank all contributors and reviewers who helped shape this benchmark.

---

## Version History

- **0.1.0** (2025-01-28) - Initial public release

## Future Roadmap

Planned features for future releases:

### Version 0.2.0 (Planned)
- Support for additional LLM providers (OpenAI, Anthropic API)
- More agent architectures (Tree-of-Thought, Self-Reflection)
- Additional benchmarks in new domains
- Improved error analysis tools
- Performance optimizations

### Version 0.3.0 (Planned)
- Multi-language SOP support
- Real API integrations (optional)
- Advanced metrics and visualizations
- Benchmark difficulty scoring
- Agent comparison dashboard

### Version 1.0.0 (Planned)
- Stable API
- Production-ready features
- Comprehensive documentation
- Enterprise support options

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/amazon/sop-bench/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amazon/sop-bench/discussions)

## License

CC-BY-NC-4.0 - See [LICENSE](LICENSE) for details.
