import axios from 'axios';
import serviceConfig from './config';

const addSource = (data = {}, params = {}) =>
  axios(
    serviceConfig({
      method: 'post',
      url: process.env.REACT_APP_SOURCES_SERVICE,
      data,
      params
    })
  );

const deleteSource = id =>
  axios(
    serviceConfig({
      method: 'delete',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}/`
    })
  );

const deleteSources = (data = []) => Promise.all(data.map(id => deleteSource(id)));

const getSources = (id = '', params = {}) =>
  axios(
    serviceConfig(
      {
        url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}`,
        params
      },
      false
    )
  );

const getSource = id => getSources(id);

const updateSource = (id, data = {}) =>
  axios(
    serviceConfig({
      method: 'put',
      url: `${process.env.REACT_APP_SOURCES_SERVICE}${id}/`,
      data
    })
  );

const sourcesService = {
  addSource,
  deleteSource,
  deleteSources,
  getSources,
  getSource,
  updateSource
};

export {
  sourcesService as default,
  sourcesService,
  addSource,
  deleteSource,
  deleteSources,
  getSources,
  getSource,
  updateSource
};
