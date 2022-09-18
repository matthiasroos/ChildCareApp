
import connexion


app = connexion.App(
    __name__,
    specification_dir='./.',
    options={'swagger_ui': False}
)

app.add_api('openapi.yaml')
app.run(port=8081)
