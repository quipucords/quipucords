import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';

import {
  Alert,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { getScans } from '../../redux/actions/scansActions';

import ScansToolbar from './scansToolbar';
import ScansEmptyState from './scansEmptyState';
import { ScanListItem } from './scanListItem';

class Scans extends React.Component {
  componentDidMount() {
    this.props.getScans();
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return (item.id + '').match(re) !== null; // Using ID for now until we get a name
      case 'status':
        return item.status === filter.value.id;
      case 'scanType':
        return item.scan_type === filter.value.id;
      default:
        return true;
    }
  }

  matchesFilters(item, filters) {
    let matches = true;

    filters.forEach(filter => {
      if (!this.matchesFilter(item, filter)) {
        matches = false;
        return false;
      }
    });
    return matches;
  }

  filterScans() {
    const { scans, activeFilters } = this.props;

    return scans.filter(item => {
      return this.matchesFilters(item, activeFilters);
    });
  }

  sortScans(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.id - item2.id; // Using ID for now until we get a name
          break;
        case 'status':
          compValue = item1.status.localeCompare(item2.status);
          if (compValue === 0) {
            compValue = item1.scan_type.localeCompare(item2.scan_type);
          }
          break;
        case 'scanType':
          compValue = item1.scan_type.localeCompare(item2.scan_type);
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
          }
          break;
        case 'sourceCount':
          compValue = item1.sources.length - item2.sources.length;
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
            if (compValue === 0) {
              compValue = item1.scan_type.localeCompare(item2.scan_type);
            }
          }
          break;
        default:
          compValue = 0;
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  renderList(items) {
    return (
      <Row>
        <ListView className="quipicords-list-view">
          {items.map((item, index) => <ScanListItem item={item} key={index} />)}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, scans } = this.props;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scans...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="danger">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (scans && scans.length) {
      let filteredScans = this.filterScans(scans);
      this.sortScans(filteredScans);

      return [
        <ScansToolbar
          totalCount={scans.length}
          filteredCount={filteredScans.length}
          key={1}
        />,
        <Grid fluid key={2}>
          {this.renderList(filteredScans)}
        </Grid>
      ];
    }
    return <ScansEmptyState />;
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  scans: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Scans.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: () => dispatch(getScans())
});

function mapStateToProps(state) {
  return {
    loading: state.scans.loading,
    scans: state.scans.data,
    loadError: state.scans.error,
    errorMessage: state.scans.errorMessage,
    activeFilters: state.scansToolbar.activeFilters,
    sortType: state.scansToolbar.sortType,
    sortAscending: state.scansToolbar.sortAscending
  };
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Scans));
