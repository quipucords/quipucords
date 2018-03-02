import axios from 'axios';

class SourcesService {
  static addSource(data = {}) {
    return axios({
      method: 'post',
      url: process.env.REACT_APP_SOURCES_SERVICE,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      data: data
    });
  }

  static deleteSource(id) {
    return axios({
      method: 'delete',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }

  static deleteSources(data = []) {
    return Promise.all.apply(this, data.map(id => this.deleteSource(id)));
  }

  static getSource(id) {
    return this.getSources(id);
  }

  static getSources(id = '', query = {}) {
    return axios({
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}`,
      params: query
    });
  }

  static updateSource(id, data = {}) {
    return axios({
      method: 'put',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}/`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      data: data
    });
  }
}

export default SourcesService;
