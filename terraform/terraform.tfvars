aws_region   = "us-east-1"
environment  = "prod"
project_name = "dio"

anthropic_model = "claude-haiku-4-5"

vercel_oidc_issuer_url = "https://oidc.vercel.com/ljhursts-projects"
vercel_oidc_thumbprint = "ab9d0263244dd0326eb67015705a667e79cfe998"
vercel_oidc_audience   = "https://vercel.com/ljhursts-projects"
vercel_oidc_subjects = [
  "owner:ljhursts-projects:project:sommething:environment:production",
  "owner:ljhursts-projects:project:sommething:environment:preview",
  "owner:ljhursts-projects:project:sommething:environment:development",
]

# Settings > Workload identity in the Claude Console
anthropic_federation = {
  rule_id            = "fdrl_01Ng9tq3G4ZaU8bDSjsCL6iZ"
  organization_id    = "7eff1b18-ebc4-4ba7-95f9-7b55fcb7356e"
  service_account_id = "svac_017J8tkSNZMLyPTr5aTdPFVX"
  workspace_id       = "wrkspc_01EuFUBWXk22cvkqe2vVzeLi"
}
