import pulumi


def register_default_tags(default_tags: dict):
    # Required to fix the current downside of default tags not updating resources when using aws_provider
    # See - https://github.com/pulumi/pulumi-aws/issues/1655
    # And - https://www.pulumi.com/blog/automatically-enforcing-aws-resource-tagging-policies/#automatically-applying-tags
    return pulumi.runtime.register_stack_transformation(
        lambda args: default_tag(args, default_tags)
    )


def default_tag(args: pulumi.ResourceTransformationArgs, default_tags: dict):
    if hasattr(args.resource, "tags"):
        args.props["tags"] = {**(args.props["tags"] or {}), **default_tags}

    return pulumi.ResourceTransformationResult(args.props, args.opts)
