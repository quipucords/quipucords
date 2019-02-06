import promiseMiddleware from 'redux-promise-middleware';
import { applyMiddleware, combineReducers, createStore } from 'redux';
import moxios from 'moxios';
import { userReducer } from '../../reducers';
import { userActions } from '..';

describe('UserActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        user: userReducer
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

  it('Should return response content for getUser method', done => {
    const store = generateStore();
    const dispatcher = userActions.getUser();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().user;

      expect(response.user.currentUser.test).toEqual('success');
      done();
    });
  });

  it('Should return response content for authorizeUser method', done => {
    const store = generateStore();
    const dispatcher = userActions.authorizeUser();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().user;

      expect(response.session.fulfilled).toEqual(true);
      expect(response.session.loggedIn).toEqual(true);
      done();
    });
  });

  it('Should return response content for logoutUser method', done => {
    const store = generateStore();
    const dispatcher = userActions.logoutUser();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().user;

      expect(response.session.fulfilled).toEqual(true);
      expect(response.session.loggedIn).toEqual(false);
      done();
    });
  });
});
