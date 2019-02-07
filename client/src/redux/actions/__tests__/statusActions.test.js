import promiseMiddleware from 'redux-promise-middleware';
import { applyMiddleware, combineReducers, createStore } from 'redux';
import moxios from 'moxios';
import { statusReducer } from '../../reducers';
import { statusActions } from '..';

describe('StatusActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        status: statusReducer
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
          test: 'success'
        }
      });
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('Should return response content for getStatus method', done => {
    const store = generateStore();
    const dispatcher = statusActions.getStatus();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().status;

      expect(response.currentStatus.test).toEqual('success');
      done();
    });
  });
});
