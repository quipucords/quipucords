import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';
import { AboutModal } from 'patternfly-react';

import { routes } from '../routes';
import Store from '../redux/store';
import Content from './content/content';
import Masthead from './masthead/masthead';
import VerticalNavigation from './verticalNavigation/verticalNavigation';

import './app.css';
import logo from '../logo.svg';

class App extends React.Component {
  constructor() {
    super();
    this.menu = routes();
  }

  render() {
    const { showAbout } = this.props;

    let closeAbout = () => Store.dispatch({ type: 'ABOUT_DIALOG_CLOSE' });

    return [
      <Masthead key="masthead" />,
      <VerticalNavigation menuItems={this.menu} key="navigation" />,
      <Content key="content" />,
      <AboutModal
        key="aboutModal"
        show={showAbout}
        onHide={closeAbout}
        productTitle="Red Hat Entitlements Reporting"
        logo={logo}
        altLogo="RH ER"
        trademarkText="Copyright (c) 2018 Red Hat Inc."
      >
        <AboutModal.Versions>
          <AboutModal.VersionItem label="Label" versionText="Version" />
        </AboutModal.Versions>
      </AboutModal>
    ];
  }
}

App.propTypes = {
  showAbout: PropTypes.bool
};

function mapStateToProps(state, ownProps) {
  return {
    showAbout: state.about.show
  };
}

export default withRouter(connect(mapStateToProps)(App));
