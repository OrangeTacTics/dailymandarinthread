import axios from 'axios';
import React, { useState } from 'react'


function ProfileLookup() {
  const [profileData, setProfileData] = useState<any>(null);

  return <>
      Learn React, Ok?
      <input className="md-search__input" onChange={async (ev) => setProfileData(await profile(ev.target.value))}/>
      <div style={{whiteSpace: "pre"}}>{JSON.stringify(profileData, null, 4)}</div>
  </>
}


async function profile(username: string) {
    const payload = {
        "query": `
            query($username: String) {
                profile(discordUsername: $username) {
                    userId
                    discordUsername
                    credit
                }
            }
        `,
        "variables": {
            "username": username,
        }
    }
    const response = await axios({
        url: "/graphql",
        method: "POST",
        data: payload,
    });
    console.log(response.data.data);
    return response.data.data;
}

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <ProfileLookup/>
      </header>
    </div>
  );
}

export default App;
