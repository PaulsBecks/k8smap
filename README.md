# k8smap

k8smap is a tool to generate a diagram a diagram text file from kubernetes resource descriptions. 
I implemented this to get a faster understanding of the resources in a given helm chart.
Also it helps me document the infrastructure automatically visually for my colleagues.

# Quick start

```
poetry add k8smap

k8smap -i filename.yaml
```

# Example
You can clone the repo and test it locally.

```
helm template example > example.yaml 
poetry run k8smap -i infratest.yaml
```

This will generate the following output to file file `output.d2`:
```
Service_pawn:pawn {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/svc.svg
  shape: image
}
Service_bishop:bishop {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/svc.svg
  shape: image
}
Pod_bishop-nginx:bishop-nginx {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/pod.svg
  shape: image
}
Deployment_nginx-deployment:nginx-deployment {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/deploy.svg
  shape: image
}
Pod_nginx-deployment:nginx-deployment {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/pod.svg
  shape: image
}
Ingress_pawn-ingress:pawn-ingress {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/ing.svg
  shape: image
}
Ingress_bishop-ingress:bishop-ingress {
  icon: https://raw.githubusercontent.com/kubernetes/community/master/icons/svg/resources/labeled/ing.svg
  shape: image
}
Service_pawn --> Pod_nginx-deployment
Service_bishop --> Pod_bishop-nginx
Deployment_nginx-deployment --> Pod_nginx-deployment
Ingress_pawn-ingress --> Service_pawn
Ingress_bishop-ingress --> Service_bishop
```

To generate an image for this graph you can run d2.
```
d2 output.d2 out.svg
```

![Visualization of the helm chart](./docs/example-diagram.png)

Or generate a mermaid flowchart.
```
mapk8s -i filename.yaml -f mermaid
```

# Components

So far the following components are implemented:

- [x] Pod
- [x] Deployment
- [x] Ingress
- [x] Service
- [x] Config Map
- [x] Network Policy
- [ ] Service Account
- [ ] Cron Job
- [ ] Job
- [ ] Secret
- [ ] Volume
- [ ] Persistent Volume
- [ ] Persistent Volume Claim

# Output formats
So far the following output languages are supported:
- [x] [D2](https://d2lang.com/tour/intro/)
- [x] [Mermaid](https://mermaid-js.github.io/mermaid/#/)

Use the `-f [d2, mermaid]` flag to specify the format.

# License
This is unclear right now and needs to be checked. 
As I am using in this code svg from Kubernetes, I first have to evaluate what license I can use.
