from dataclasses import dataclass


@dataclass(frozen=True)
class TechnologyDefinition:
    """A tracked technology and the GitHub repositories that represent it."""

    slug: str
    name: str
    category: str
    description: str
    website_url: str
    repositories: tuple[str, ...]


CATALOG: tuple[TechnologyDefinition, ...] = (
    TechnologyDefinition(
        slug="linux",
        name="Linux",
        category="operating-system",
        description="The open source kernel that underpins most servers, containers and clouds.",
        website_url="https://www.kernel.org",
        repositories=("torvalds/linux",),
    ),
    TechnologyDefinition(
        slug="python",
        name="Python",
        category="language",
        description="General purpose language widely used for automation and tooling.",
        website_url="https://www.python.org",
        repositories=("python/cpython",),
    ),
    TechnologyDefinition(
        slug="git",
        name="Git",
        category="version-control",
        description="Distributed version control system.",
        website_url="https://git-scm.com",
        repositories=("git/git",),
    ),
    TechnologyDefinition(
        slug="docker",
        name="Docker",
        category="containers",
        description="Container engine and tooling for building and running containers.",
        website_url="https://www.docker.com",
        repositories=("moby/moby", "docker/compose"),
    ),
    TechnologyDefinition(
        slug="kubernetes",
        name="Kubernetes",
        category="orchestration",
        description="Container orchestration platform for automating deployment and scaling.",
        website_url="https://kubernetes.io",
        repositories=("kubernetes/kubernetes", "kubernetes-sigs/kind"),
    ),
    TechnologyDefinition(
        slug="helm",
        name="Helm",
        category="packaging",
        description="Package manager for Kubernetes applications.",
        website_url="https://helm.sh",
        repositories=("helm/helm",),
    ),
    TechnologyDefinition(
        slug="openshift",
        name="OpenShift",
        category="orchestration",
        description="Enterprise Kubernetes platform; OKD is its community distribution.",
        website_url="https://www.okd.io",
        repositories=("okd-project/okd", "openshift/installer"),
    ),
    TechnologyDefinition(
        slug="argo-cd",
        name="Argo CD",
        category="gitops",
        description="Declarative GitOps continuous delivery for Kubernetes.",
        website_url="https://argo-cd.readthedocs.io",
        repositories=("argoproj/argo-cd",),
    ),
    TechnologyDefinition(
        slug="github-actions",
        name="GitHub Actions",
        category="ci-cd",
        description="CI/CD workflows integrated into GitHub; tracked through its runner.",
        website_url="https://github.com/features/actions",
        repositories=("actions/runner",),
    ),
    TechnologyDefinition(
        slug="terraform",
        name="Terraform",
        category="infrastructure-as-code",
        description="Infrastructure as code tool; OpenTofu is its open source fork.",
        website_url="https://www.terraform.io",
        repositories=("hashicorp/terraform", "opentofu/opentofu"),
    ),
    TechnologyDefinition(
        slug="ansible",
        name="Ansible",
        category="configuration-management",
        description="Agentless automation for configuration management and orchestration.",
        website_url="https://www.ansible.com",
        repositories=("ansible/ansible",),
    ),
    TechnologyDefinition(
        slug="postgresql",
        name="PostgreSQL",
        category="database",
        description="Advanced open source relational database.",
        website_url="https://www.postgresql.org",
        repositories=("postgres/postgres",),
    ),
    TechnologyDefinition(
        slug="prometheus",
        name="Prometheus",
        category="monitoring",
        description="Metrics collection, storage and alerting toolkit.",
        website_url="https://prometheus.io",
        repositories=("prometheus/prometheus",),
    ),
    TechnologyDefinition(
        slug="grafana",
        name="Grafana",
        category="monitoring",
        description="Dashboards and visualization for metrics, logs and traces.",
        website_url="https://grafana.com",
        repositories=("grafana/grafana",),
    ),
    TechnologyDefinition(
        slug="ollama",
        name="Ollama",
        category="ai",
        description="Runtime for running large language models locally.",
        website_url="https://ollama.com",
        repositories=("ollama/ollama",),
    ),
)
