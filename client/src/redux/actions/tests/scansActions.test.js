import configureMockStore from 'redux-mock-store';
import promiseMiddleware from 'redux-promise-middleware';
import moxios from 'moxios';
import expect from 'expect';

import { scansTypes } from '../../constants';
import * as actions from '../scansActions';

const middlewares = [promiseMiddleware()];
const mockStore = configureMockStore(middlewares);

describe('ScansActions', function() {
  beforeEach(() => {
    process.env.REACT_APP_ENV = 'development';
    process.env.REACT_APP_CREDENTIALS_SERVICE = '/api/v1/credentials/';
    process.env.REACT_APP_FACTS_SERVICE = '/api/v1/facts/';
    process.env.REACT_APP_REPORTS_SERVICE = '/api/v1/reports/';

    process.env.REACT_APP_SCANS_SERVICE = '/api/v1/scans/';
    process.env.REACT_APP_SCANS_SERVICE_CANCEL = '/api/v1/scans/{0}/cancel/';
    process.env.REACT_APP_SCANS_SERVICE_PAUSE = '/api/v1/scans/{0}/pause/';
    process.env.REACT_APP_SCANS_SERVICE_RESTART = '/api/v1/scans/{0}/restart/';
    process.env.REACT_APP_SCANS_SERVICE_RESULTS = '/api/v1/scans/{0}/results/';

    process.env.REACT_APP_SOURCES_SERVICE = '/api/v1/sources/';

    process.env.REACT_APP_AUTH_TOKEN = 'csrfspoof';
    process.env.REACT_APP_AUTH_HEADER = 'X-CSRFToken';

    moxios.install();
  });

  afterEach(() => {
    moxios.uninstall();
  });

  const getScansMock = {
    body: {
      data: {
        results: [
          {
            name: '1',
            id: 1
          },
          {
            name: '5',
            id: 5
          },
          {
            name: '6',
            id: 6
          },
          {
            name: '7',
            id: 7
          }
        ]
      }
    },
    headers: { 'content-type': 'application/json' }
  };

  it('creates GET_SCANS_FULFILLED when adding source has been done', () => {
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: getScansMock
      });
    });

    const expectedActions = [scansTypes.GET_SCANS_PENDING, scansTypes.GET_SCANS_FULFILLED];
    const store = mockStore({ todos: [] });

    return store.dispatch(actions.dispatchObjects.getScans()).then(() => {
      const dispatchedActions = store.getActions();
      const actionTypes = dispatchedActions.map(action => action.type);

      expect(actionTypes).toEqual(expectedActions);
    });
  });
});
