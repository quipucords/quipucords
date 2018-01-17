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

import { getSources } from '../../redux/actions/sourcesActions';

import SourcesToolbar from './sourcesToolbar';
import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';

class Sources extends React.Component {
  componentDidMount() {
    this.props.getSources();
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return item.name.match(re) !== null;
      case 'sourceType':
        return item.source_type === filter.value.id;
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

  filterSources() {
    const { sources, activeFilters } = this.props;

    return sources.filter(item => {
      return this.matchesFilters(item, activeFilters);
    });
  }

  sortSources(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.name.localeCompare(item2.name);
          break;
        case 'sourceType':
          compValue = item1.source_type.localeCompare(item2.source_type);
          break;
        case 'hostCount':
          compValue = item1.hosts.length - item2.hosts.length;
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
          {items.map((item, index) => (
            <SourceListItem item={item} key={index} />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, sources } = this.props;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="danger">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (sources && sources.length) {
      let filteredSources = this.filterSources(sources);
      this.sortSources(filteredSources);

      return [
        <SourcesToolbar
          totalCount={sources.length}
          filteredCount={filteredSources.length}
          key={1}
        />,
        <Grid fluid key={2}>
          {this.renderList(filteredSources)}
        </Grid>
      ];
    }
    return <SourcesEmptyState />;
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  sources: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Sources.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

function mapStateToProps(state) {
  return {
    loading: state.sources.loading,
    sources: state.sources.data,
    loadError: state.sources.error,
    errorMessage: state.sources.errorMessage,
    activeFilters: state.sourcesToolbar.activeFilters,
    sortType: state.sourcesToolbar.sortType,
    sortAscending: state.sourcesToolbar.sortAscending
  };
}

export default withRouter(
  connect(mapStateToProps, mapDispatchToProps)(Sources)
);
