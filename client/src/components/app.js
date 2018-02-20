import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { connect } from 'react-redux';
import { withRouter } from 'react-router';

import {
  Alert,
  EmptyState,
  Modal,
  VerticalNav
} from 'patternfly-react';

import { routes } from '../routes';

import About from './about/about';
import Content from './content/content';
import ToastNotificationsList from './toastNotificationList/toastNotificatinsList';
import ConfirmationModal from './confirmationModal/confirmationModal';
import MastheadOptions from './mastheadOptions/mastheadOptions';

import productTitle from '../styles/images/title.svg';
import { authorizeUser } from '../redux/actions/userActions';

class App extends React.Component {
  constructor() {
    super();
    this.menu = routes();
  }

  componentDidMount() {
    this.props.authorizeUser();
  }

  navigateTo(path) {
    const { history } = this.props;
    history.push(path);
  }

  renderMenuItems() {
    const { location } = this.props;

    let activeItem = this.menu.find(item =>
      _.startsWith(location.pathname, item.to)
    );

    return this.menu.map(item => {
      return (
        <VerticalNav.Item
          key={item.to}
          title={item.title}
          iconClass={item.iconClass}
          active={item === activeItem || (!activeItem && item.redirect)}
          onClick={() => this.navigateTo(item.to)}
        />
      );
    });
  }

  renderContent() {
    const { session } = this.props;

    if (session.error) {
      return (
        <EmptyState className="full-page-blank-slate">
          <Alert type="error">
            <span>Login error: {session.errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (session.pending || !session.fulfilled || (!session.loggedIn && !session.wasLoggedIn)) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl"/>
            <div className="text-center">Logging in...</div>
          </Modal.Body>
        </Modal>
      );
    }

    return (
      <React.Fragment>
        <Content />
        <ToastNotificationsList key="toastList" />
        <ConfirmationModal key="confirmationModal" />
        <About />
      </React.Fragment>
    );
  }

  render() {
    const { session } = this.props;

    if (!session.loggedIn && session.wasLoggedIn) {
      window.location = '/logout';
    }

    return (
      <div className="layout-pf layout-pf-fixed">
        <VerticalNav persistentSecondary={false}>
          <VerticalNav.Masthead>
            <VerticalNav.Brand titleImg={productTitle} />
            <MastheadOptions />
          </VerticalNav.Masthead>
          {this.renderMenuItems()}
        </VerticalNav>
        <div className="container-pf-nav-pf-vertical">
          {this.renderContent()}
        </div>
      </div>
    );
  }
}

App.propTypes = {
  authorizeUser: PropTypes.func,
  session: PropTypes.object,
  location: PropTypes.object,
  history: PropTypes.shape({
    push: PropTypes.func.isRequired
  }).isRequired
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  authorizeUser: () => dispatch(authorizeUser())
});

function mapStateToProps(state, ownProps) {
  return {
    session: state.user.session
  };
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(App));
