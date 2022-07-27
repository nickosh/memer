# Memer

Telegram bot which you can send meme pictures to. All collected memes are gathered into the database and broadcast as a slideshow on a web page, thanks to the built-in web server.

Thus, you can easily and cheerfully exchange pictures in a single feed. Initially, I created this project for my office, where colleagues can anonymously drop their memes (or any other pictures) to the bot, and then everyone can watch a slideshow of memes on the office TV. Bot support voting for content - thumbs up/down and for deleting meme (need 3 votes from different people).

### Features

- Gather your shiny memes in one place;
- Browser-based meme slideshow for any big screen (tv-compability);
- Telegram bot inside: as easy as drop any meme right in chat, also vote and report features;

### Deploy
#### How to start
- Needs https certificate support for telegram bot webhook functionality.

1. Starts for the first time, then shutdown. Go to **data** volume and edit **config.json**:

-- `"param":"bot_api_key","value":"place_your_telegram_bot_API_TOKEN_here"` 

-- `"param":"web_host","value":"your_domain_here.com"` 

-- `"param":"web_port","value":"80"` 

-- `"param":"app_site_header","value":"Frontend header here"`

-- `"param":"app_site_title","value":"Your site title (top left corner)"`

-- `"param":"app_site_botname","value":"@your_telegram_bot"`

2. Starts again. Now telegram bot should work. Try it with **/start** command.
3. Upload few memes via telegram bot (just drop memes in chat like any photo). Restart app.
4. Should fully works now.

#### Docker-compose example
    version: "3.3"
    
    services:
    
      traefik:
        image: "traefik:v2.0.0-rc3"
        container_name: "traefik"
        command:
          #- "--log.level=DEBUG"
          - "--global.sendAnonymousUsage=false"
          - "--api.insecure=true"
          - "--providers.docker=true"
          - "--providers.docker.exposedbydefault=false"
          - "--entrypoints.websecure.address=:443"
          - "--certificatesresolvers.mytlschallenge.acme.tlschallenge=true"
          #- "--certificatesresolvers.mytlschallenge.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
          - "--certificatesresolvers.mytlschallenge.acme.email=postmaster@mydomain.com"
          - "--certificatesresolvers.mytlschallenge.acme.storage=/letsencrypt/acme.json"
        ports:
          - "443:443"
          - "8080:8080"
        volumes:
          - "./letsencrypt:/letsencrypt"
          - "/var/run/docker.sock:/var/run/docker.sock:ro"
    
      memer:
        image: "docker.pkg.github.com/nickosh/memer/memer:latest"
        container_name: "memer"
        labels:
          - "traefik.enable=true"
          - "traefik.http.routers.memer.rule=Host(`mydomain.com`)"
          - "traefik.http.routers.memer.entrypoints=websecure"
          - "traefik.http.routers.memer.tls.certresolver=mytlschallenge"
        ports:
          - "80:80"
        volumes:
          - "/opt/memer/data:/memer/data"
          - "/opt/memer/imgs:/memer/imgs"
          - "/var/run/docker.sock:/var/run/docker.sock:ro"
