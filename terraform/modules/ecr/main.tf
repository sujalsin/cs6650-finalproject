resource "aws_ecr_repository" "repo" {
  name                 = "${var.project}-repo"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}
