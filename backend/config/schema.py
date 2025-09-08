import graphene
class Query(graphene.ObjectType):
hello = graphene.String()
def resolve_hello(self, info):
    return "Hello from ReactDjango Hub Medical!"
class Mutation(graphene.ObjectType):
pass
schema = graphene.Schema(query=Query, mutation=Mutation)
