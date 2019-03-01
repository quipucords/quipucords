import moxios from 'moxios';
import promiseMiddleware from 'redux-promise-middleware';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import { credentialsReducer } from '../../reducers';
import { credentialsActions } from '..';
import apiTypes from '../../../constants/apiConstants';

describe('CredentialsActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        credentials: credentialsReducer
      }),
      applyMiddleware(...middleware)
    );

  beforeEach(() => {
    moxios.install();

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: {
          test: 'success',
          [apiTypes.API_RESPONSE_CREDENTIALS_RESULTS]: ['success']
        }
      });
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('Should return response content for addAccount method', done => {
    const store = generateStore();
    const dispatcher = credentialsActions.addCredential();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().credentials;

      expect(response.update.credential.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for getCredential method', () => {
    const dispatcher = credentialsActions.getCredential();

    expect(dispatcher).toBeDefined();
  });

  it('Should return response content for getCredentials method', done => {
    const store = generateStore();
    const dispatcher = credentialsActions.getCredentials();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().credentials;

      expect(response.view.credentials[0]).toEqual('success');
      done();
    });
  });

  it('Should return response content for updateCredential method', done => {
    const store = generateStore();
    const dispatcher = credentialsActions.updateCredential();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().credentials;

      expect(response.update.credential.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for deleteCredential method', done => {
    const store = generateStore();
    const dispatcher = credentialsActions.deleteCredential();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().credentials;

      expect(response.update.delete).toEqual(true);
      done();
    });
  });

  it('Should return response content for deleteCredentials method', done => {
    const store = generateStore();
    const dispatcher = credentialsActions.deleteCredentials();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().credentials;

      expect(response.update.delete).toEqual(true);
      done();
    });
  });
});
