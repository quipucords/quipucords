import axios from 'axios';
import serviceConfig from './config';

const addCredential = (data = {}) =>
  axios(
    serviceConfig({
      method: 'post',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}`,
      data
    })
  );

const deleteCredential = id =>
  axios(
    serviceConfig({
      method: 'delete',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}/`
    })
  );

const deleteCredentials = (data = []) =>
  Promise.all(data.map(id => deleteCredential(id))).then(success => new Promise(resolve => resolve({ data: success })));

const getCredentials = (id = '', params = {}) =>
  axios(
    serviceConfig(
      {
        url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}`,
        params
      },
      false
    )
  );

const getCredential = id => getCredentials(id);

const updateCredential = (id, data = {}) =>
  axios(
    serviceConfig({
      method: 'put',
      url: `${process.env.REACT_APP_CREDENTIALS_SERVICE}${id}/`,
      data
    })
  );

const credentialsService = {
  addCredential,
  deleteCredential,
  deleteCredentials,
  getCredential,
  getCredentials,
  updateCredential
};

export {
  credentialsService as default,
  credentialsService,
  addCredential,
  deleteCredential,
  deleteCredentials,
  getCredential,
  getCredentials,
  updateCredential
};
