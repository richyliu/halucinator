FROM halucinator_openplc:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tmux curl

ENV NON_INTERACTIVE=true
ENV FORCE_INSTALL=true
RUN curl -sL https://raw.githubusercontent.com/richyliu/config/8787e56939d21e0cc88a0b3658721e1f39417be1/init_linux.sh | bash
