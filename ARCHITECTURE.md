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


/data/

    Static data used by DMT. It contains the following subdirectories:

    exams/

        Contains the JSON files which power the HSK exams.


/dmt\_chairmanmao/

    The former monolithic Python implemtation of the ChairmanMao bot. Deprecated.


/cogs/

    A collection of scripts which read from the Redis events stream and issues commands back to
    the server.


/dmt\_dailymandarinthreadinfo/

    The static HTML server code for https://dailymandarinthread.info/.


/dmt\_graphql/

    The former GraphQL server to control the bot which was located at
    https://dailymandarinthread.info/graphql. Deprecated.


/dmt\_profiles/

    An experimental page to display user profiles which were to be located at
    https://dailymandarinthread.info/profile. Deprecated.


/dmt\_auth/

    The former auth server. Currently not in use.
