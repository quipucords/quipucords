import React, { Component } from 'react';
import Store from '../../redux/store';

import { ButtonGroup, DropdownButton, MenuItem } from 'react-bootstrap';
import './masthead.css';
import { aboutTypes, navigationBarTypes } from '../../redux/constants';

class NavBar extends Component {
  render() {
    let toggleCollapse = () =>
      Store.dispatch({ type: navigationBarTypes.NAV_TOGGLE_COLLAPSE });
    let showAbout = () =>
      Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_OPEN });

    return (
      <nav className="navbar navbar-pf-vertical">
        <div className="navbar-header">
          <button
            type="button"
            className="navbar-toggle"
            onClick={toggleCollapse}
          >
            <span className="sr-only">Toggle navigation</span>
            <span className="icon-bar" />
            <span className="icon-bar" />
            <span className="icon-bar" />
          </button>
          <span className="navbar-brand">
            <img
              className="navbar-brand-icon"
              src="/assets/img/logo.svg"
              alt=""
            />
            <img
              className="navbar-brand-name navbar-brand-txt"
              src="/public/assets/img/brand-alt.svg"
              alt="Red Hat Entitlements Reporting"
            />
          </span>
        </div>
        <nav className="collapse navbar-collapse">
          <ButtonGroup className="nav navbar-nav navbar-right navbar-iconic navbar-utility">
            <span className=" btn-group dropdown nav-item-iconic ">
              <DropdownButton
                className="fa pficon-help"
                title=""
                id="nav-help-dropdown"
              >
                <MenuItem>Help</MenuItem>
                <MenuItem onClick={showAbout}>About</MenuItem>
              </DropdownButton>
            </span>
          </ButtonGroup>
        </nav>
      </nav>
    );
  }
}

export default NavBar;
