/charmanmao/

    The Rust implementation of ChairmanMao. Builds the following binaries:

        chairmanmao-cli

            A command-line utility which provides some basic server moderation tools for DMT. It
            only makes use of the Discord HTTP API and does not connect to the Discord Gateway.

        chairmanmao-eventer

            A server which connects to the Discord Gateway and listens to all incoming events
            Discord sends. It logs these events to a Redis stream for consumption by other
            components.

        chairmanmao

            A server which connects to the Discord Gateway and responds to various kinds of events.
            Handles social credit, role assignment via tags, renaming users, and a few other
            features. Moving to be deprecated by chairmanmao-eventer.

        draw

            A command-line utility for testing the character-drawing code.

        exam

            A command-line utility for testing the exam code.

        chairmanmao-examiner

            A server which connects to the Discord Gateway and responds to events pertaining to
            the /exam command.
