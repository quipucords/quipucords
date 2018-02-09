import jquery from 'jquery';

class SourcesService {
  static addSource(data = {}) {
    return fetch(process.env.REACT_APP_SOURCES_SERVICE, {
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

  static deleteSource(id) {
    return fetch(`${process.env.REACT_APP_SOURCES_SERVICE}${id}`, {
      method: 'DELETE'
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }

  static deleteSources(data = []) {
    return Promise.all.apply(this, data.map(id => this.deleteSource(id)));
  }

  static getSource(id) {
    return this.getSources(id);
  }

  static getSources(id = '', query = {}) {
    let queryStr = jquery.param(query);

    if (queryStr.length) {
      queryStr = `?${queryStr}`;
    }

    return fetch(
      `${process.env.REACT_APP_SOURCES_SERVICE}${id}${queryStr}`
    ).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }

  static updateSource(id, data = {}) {
    return fetch(`${process.env.REACT_APP_SOURCES_SERVICE}${id}`, {
      method: 'PUT',
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

export default SourcesService;
