class FactsService {
  static addFacts(data = {}) {
    return fetch(process.env.REACT_APP_FACTS_SERVICE, {
      method: 'POST',
      headers: new Headers({
        'Content-Type': 'application/json'
      }),
      body: JSON.stringify(data)
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }
}

export default FactsService;
